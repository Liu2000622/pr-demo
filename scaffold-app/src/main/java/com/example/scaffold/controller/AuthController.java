package com.example.scaffold.controller;

import com.example.scaffold.entity.User;
import com.example.scaffold.repository.UserRepository;
import com.example.scaffold.security.ShiroAuthFilter;
import com.example.scaffold.service.CaptchaService;
import com.example.scaffold.service.PasswordService;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.shiro.SecurityUtils;
import org.apache.shiro.authc.AuthenticationException;
import org.apache.shiro.authc.UsernamePasswordToken;
import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.subject.Subject;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Authentication endpoints driven by Apache Shiro.
 * <p>
 * Endpoints:
 * <ul>
 *   <li>{@code POST /api/login} &mdash; authenticate with username, password and a captcha</li>
 *   <li>{@code POST /api/register} &mdash; register a new user (username + password + captcha)</li>
 *   <li>{@code GET /api/captcha} &mdash; issue a fresh 6-char alphanumeric captcha image</li>
 *   <li>{@code POST /api/logout} &mdash; invalidate the current session</li>
 *   <li>{@code GET /api/me} &mdash; report the current (possibly anonymous) subject</li>
 * </ul>
 * <p>
 * Default seeded account: {@code admin} / {@code admin123}.
 */
@RestController
@RequestMapping("/api")
public class AuthController {

    private static final int USERNAME_MIN = 3;
    private static final int USERNAME_MAX = 32;
    private static final int PASSWORD_MIN = 6;
    private static final int PASSWORD_MAX = 64;

    private final SecurityManager securityManager;
    private final UserRepository userRepository;
    private final PasswordService passwordService;
    private final CaptchaService captchaService;

    public AuthController(SecurityManager securityManager,
                          UserRepository userRepository,
                          PasswordService passwordService,
                          CaptchaService captchaService) {
        this.securityManager = securityManager;
        this.userRepository = userRepository;
        this.passwordService = passwordService;
        this.captchaService = captchaService;
    }

    public record LoginRequest(String username, String password, String captchaId, String captcha) {
    }

    public record RegisterRequest(String username, String password, String captchaId, String captcha) {
    }

    /**
     * Issues a fresh captcha. Returns the captcha id (to be sent back on
     * login/register) and the rendered image as a base64 data URI. The captcha text
     * itself is never exposed to the client.
     */
    @GetMapping("/captcha")
    public ResponseEntity<?> captcha() {
        CaptchaService.Captcha captcha = captchaService.generate();
        return ResponseEntity.ok(Map.of(
                "captchaId", captcha.id(),
                "image", captcha.image()));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request, HttpServletResponse response) {
        if (!captchaService.verify(request.captchaId(), request.captcha())) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("code", 400, "message", "Invalid or expired captcha"));
        }

        Subject subject = new Subject.Builder(securityManager).sessionCreationEnabled(true).buildSubject();
        try {
            subject.login(new UsernamePasswordToken(request.username(), request.password(), false));
        } catch (AuthenticationException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("code", 401, "message", "Invalid username or password"));
        }
        Object sessionId = subject.getSession().getId();
        addSessionCookie(response, sessionId == null ? null : sessionId.toString(), 30 * 60);
        return ResponseEntity.ok(Map.of(
                "username", subject.getPrincipal(),
                "sessionId", sessionId == null ? "" : sessionId));
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegisterRequest request) {
        if (!captchaService.verify(request.captchaId(), request.captcha())) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("code", 400, "message", "Invalid or expired captcha"));
        }

        String username = request.username() == null ? "" : request.username().trim();
        String password = request.password() == null ? "" : request.password();
        if (username.length() < USERNAME_MIN || username.length() > USERNAME_MAX) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("code", 400, "message",
                            "Username must be between " + USERNAME_MIN + " and " + USERNAME_MAX + " characters"));
        }
        if (password.length() < PASSWORD_MIN || password.length() > PASSWORD_MAX) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("code", 400, "message",
                            "Password must be between " + PASSWORD_MIN + " and " + PASSWORD_MAX + " characters"));
        }
        if (userRepository.countByUsername(username) > 0) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("code", 409, "message", "Username already exists"));
        }

        User user = new User();
        user.setUsername(username);
        String salt = passwordService.generateSalt();
        user.setSalt(salt);
        user.setPassword(passwordService.hashPassword(password, salt));
        user.setRole("user");
        userRepository.save(user);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("code", 201, "message", "User registered successfully", "username", username));
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpServletResponse response) {
        try {
            SecurityUtils.getSubject().logout();
        } catch (Exception ignored) {
            // best effort: clear the cookie regardless
        }
        addSessionCookie(response, "", 0);
        return ResponseEntity.ok(Map.of("message", "logged out"));
    }

    @GetMapping("/me")
    public ResponseEntity<?> me() {
        Subject subject = SecurityUtils.getSubject();
        return ResponseEntity.ok(Map.of(
                "username", subject.getPrincipal(),
                "authenticated", subject.isAuthenticated()));
    }

    private void addSessionCookie(HttpServletResponse response, String value, int maxAge) {
        Cookie cookie = new Cookie(ShiroAuthFilter.SESSION_COOKIE_NAME, value);
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge(maxAge);
        response.addCookie(cookie);
    }
}
