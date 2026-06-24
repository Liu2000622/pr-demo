package com.example.scaffold.service;

import org.apache.shiro.crypto.hash.Sha256Hash;
import org.springframework.stereotype.Component;

import java.security.SecureRandom;
import java.util.HexFormat;

/**
 * Password hashing helpers built on top of Shiro's {@link Sha256Hash}.
 * <p>
 * Passwords are salted with a per-user random salt and hashed with SHA-256 over
 * {@value #ITERATIONS} iterations. The same algorithm, salt and iteration count are
 * used by {@link com.example.scaffold.security.JpaRealm} (via its
 * {@link org.apache.shiro.authc.credential.HashedCredentialsMatcher}) so that submitted
 * passwords can be verified against the stored hash.
 */
@Component
public class PasswordService {

    /** Number of hash iterations; must match the {@code HashedCredentialsMatcher}. */
    public static final int ITERATIONS = 1024;

    private static final int SALT_BYTES = 16;

    public String generateSalt() {
        byte[] bytes = new byte[SALT_BYTES];
        new SecureRandom().nextBytes(bytes);
        return HexFormat.of().formatHex(bytes);
    }

    public String hashPassword(String plainPassword, String salt) {
        return new Sha256Hash(plainPassword, salt, ITERATIONS).toHex();
    }
}
