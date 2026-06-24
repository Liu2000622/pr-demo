package com.example.scaffold.service;

import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory captcha service producing 6-character, alphanumeric captchas
 * (letters and digits, with visually ambiguous characters excluded).
 * <p>
 * Each generated captcha is identified by a random id and stored server-side with a
 * TTL. Verification is single-use: a captcha is consumed the moment it is checked,
 * regardless of whether the answer was right, so it cannot be replayed. The captcha
 * text is never sent to the client &mdash; only a rendered PNG image (base64) is.
 * <p>
 * The store is an in-memory {@link ConcurrentHashMap} which is sufficient for this
 * single-instance scaffold. For a multi-instance deployment it would be backed by a
 * shared cache (e.g. Redis).
 */
@Component
public class CaptchaService {

    /** Length of the captcha text. */
    public static final int CAPTCHA_LENGTH = 6;

    private static final long TTL_MILLIS = 5 * 60 * 1000L;
    private static final int IMAGE_WIDTH = 160;
    private static final int IMAGE_HEIGHT = 48;

    // Exclude 0/O/1/I/l to avoid human confusion.
    private static final char[] ALPHABET =
            "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz".toCharArray();

    private static final Color BACKGROUND = new Color(245, 248, 252);

    private final SecureRandom random = new SecureRandom();
    private final Map<String, Entry> store = new ConcurrentHashMap<>();

    /**
     * Generates a fresh captcha.
     *
     * @return the captcha id, its plain text (server-side only) and the rendered image
     *         as a base64 data URI.
     */
    public Captcha generate() {
        String text = randomText();
        String id = randomId();
        String image = renderImage(text);
        store.put(id, new Entry(text, System.currentTimeMillis() + TTL_MILLIS));
        cleanup();
        return new Captcha(id, text, image);
    }

    /**
     * Verifies (and consumes) the captcha identified by {@code captchaId}.
     *
     * @param captchaId the id returned by {@link #generate()}
     * @param input     the user's answer; compared case-insensitively
     * @return {@code true} if the answer matches and the captcha had not expired
     */
    public boolean verify(String captchaId, String input) {
        if (captchaId == null || input == null || input.isBlank()) {
            return false;
        }
        Entry entry = store.remove(captchaId); // single use
        if (entry == null) {
            return false;
        }
        if (System.currentTimeMillis() > entry.expiresAt) {
            return false;
        }
        return entry.text.equalsIgnoreCase(input.trim());
    }

    private String randomText() {
        char[] buf = new char[CAPTCHA_LENGTH];
        for (int i = 0; i < buf.length; i++) {
            buf[i] = ALPHABET[random.nextInt(ALPHABET.length)];
        }
        return new String(buf);
    }

    private String randomId() {
        byte[] bytes = new byte[16];
        random.nextBytes(bytes);
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private String renderImage(String text) {
        BufferedImage image = new BufferedImage(IMAGE_WIDTH, IMAGE_HEIGHT, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(BACKGROUND);
            g.fillRect(0, 0, IMAGE_WIDTH, IMAGE_HEIGHT);

            // Noise lines.
            for (int i = 0; i < 6; i++) {
                g.setColor(new Color(random.nextInt(180), random.nextInt(180), random.nextInt(180)));
                g.setStroke(new BasicStroke(1.2f));
                g.drawLine(random.nextInt(IMAGE_WIDTH), random.nextInt(IMAGE_HEIGHT),
                        random.nextInt(IMAGE_WIDTH), random.nextInt(IMAGE_HEIGHT));
            }

            // Characters.
            g.setFont(new Font("SansSerif", Font.BOLD, 28));
            int x = 10;
            for (int i = 0; i < text.length(); i++) {
                g.setColor(new Color(random.nextInt(120), random.nextInt(120), random.nextInt(120)));
                double angle = (random.nextDouble() - 0.5) * 0.6;
                g.rotate(angle, x, 34);
                g.drawChars(new char[]{text.charAt(i)}, 0, 1, x, 34);
                g.rotate(-angle, x, 34);
                x += 24;
            }

            // Speckle noise.
            for (int i = 0; i < 40; i++) {
                g.setColor(new Color(random.nextInt(200), random.nextInt(200), random.nextInt(200)));
                g.fillRect(random.nextInt(IMAGE_WIDTH), random.nextInt(IMAGE_HEIGHT), 1, 1);
            }
        } finally {
            g.dispose();
        }

        try (ByteArrayOutputStream baos = new ByteArrayOutputStream()) {
            ImageIO.write(image, "png", baos);
            return "data:image/png;base64," + Base64.getEncoder().encodeToString(baos.toByteArray());
        } catch (IOException e) {
            // ImageIO.write on an in-memory stream does not throw in practice.
            throw new IllegalStateException("Failed to render captcha image", e);
        }
    }

    /** Drops expired entries; cheap best-effort cleanup run on each generate(). */
    private void cleanup() {
        long now = System.currentTimeMillis();
        Iterator<Map.Entry<String, Entry>> it = store.entrySet().iterator();
        while (it.hasNext()) {
            if (now > it.next().getValue().expiresAt) {
                it.remove();
            }
        }
    }

    /** A generated captcha: its id, plain text and rendered image. */
    public record Captcha(String id, String text, String image) {
    }

    private static final class Entry {
        final String text;
        final long expiresAt;

        Entry(String text, long expiresAt) {
            this.text = text;
            this.expiresAt = expiresAt;
        }
    }
}
