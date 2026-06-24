package com.example.scaffold.controller;

import com.example.scaffold.security.ShiroAuthFilter;
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
 * Default seeded account: {@code admin} / {@code admin123}.
 */
@RestController
@RequestMapping("/api")
public class AuthController {

    private final SecurityManager securityManager;

    public AuthController(SecurityManager securityManager) {
        this.securityManager = securityManager;
    }

    public record LoginRequest(String username, String password) {
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request, HttpServletResponse response) {
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
