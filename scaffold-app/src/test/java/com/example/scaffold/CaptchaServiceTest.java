package com.example.scaffold;

import com.example.scaffold.service.CaptchaService;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for {@link CaptchaService}: captcha format, successful verification,
 * case-insensitivity, wrong answer, and single-use semantics.
 */
class CaptchaServiceTest {

    private final CaptchaService captchaService = new CaptchaService();

    @Test
    void generatedCaptchaHasExpectedShape() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captcha.id()).isNotBlank();
        assertThat(captcha.text()).hasSize(CaptchaService.CAPTCHA_LENGTH);
        assertThat(captcha.text()).matches("[23456789A-Za-z]{6}");
        assertThat(captcha.image()).startsWith("data:image/png;base64,");
    }

    @Test
    void verifyAcceptsCorrectTextCaseInsensitively() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captchaService.verify(captcha.id(), captcha.text())).isTrue();
    }

    @Test
    void verifyAcceptsLowercasedText() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captchaService.verify(captcha.id(), captcha.text().toLowerCase())).isTrue();
    }

    @Test
    void verifyRejectsWrongText() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captchaService.verify(captcha.id(), "WRONG!")).isFalse();
    }

    @Test
    void verifyRejectsUnknownId() {
        assertThat(captchaService.verify("does-not-exist", "anything")).isFalse();
    }

    @Test
    void verifyRejectsNullAndBlankInput() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captchaService.verify(null, captcha.text())).isFalse();
        assertThat(captchaService.verify(captcha.id(), null)).isFalse();
        assertThat(captchaService.verify(captcha.id(), "  ")).isFalse();
    }

    @Test
    void captchaIsConsumedAfterVerification() {
        CaptchaService.Captcha captcha = captchaService.generate();
        assertThat(captchaService.verify(captcha.id(), captcha.text())).isTrue();
        // A second verification with the same id must fail (single use).
        assertThat(captchaService.verify(captcha.id(), captcha.text())).isFalse();
    }
}
