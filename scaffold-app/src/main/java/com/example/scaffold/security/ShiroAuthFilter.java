package com.example.scaffold.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.subject.Subject;
import org.apache.shiro.util.ThreadContext;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * Jakarta Servlet filter that wires Shiro's authentication core into a Spring Boot 3
 * (Jakarta) application.
 * <p>
 * Because the official {@code shiro-spring-boot-web-starter} is javax-based and thus
 * incompatible with Spring Boot 3, this filter provides the small amount of web plumbing
 * Shiro normally provides itself: it resolves the Shiro {@link Subject} for each request
 * (from the session cookie when present) and enforces the configured filter chain
 * ({@code anon} / {@code authc}).
 * <p>
 * Each filter-chain entry maps an Ant-style pattern to an action. Patterns are evaluated
 * in declaration order and the first match wins; any unmatched path defaults to
 * {@code authc}. This ensures no endpoint is accidentally left without an explicit
 * authorization rule.
 */
public class ShiroAuthFilter extends OncePerRequestFilter {

    /** Name of the cookie that carries the Shiro session id. */
    public static final String SESSION_COOKIE_NAME = "SHIRO_SESSION_ID";

    private static final String ACTION_ANON = "anon";
    private static final String ACTION_AUTHC = "authc";

    private final SecurityManager securityManager;
    private final List<Map.Entry<String, String>> chain;

    public ShiroAuthFilter(SecurityManager securityManager, Map<String, String> filterChain) {
        this.securityManager = securityManager;
        this.chain = List.copyOf(filterChain.entrySet());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        Subject subject = resolveSubject(request);
        ThreadContext.bind(securityManager);
        ThreadContext.bind(subject);
        try {
            String action = matchAction(request.getRequestURI());
            if (ACTION_AUTHC.equals(action) && !subject.isAuthenticated()) {
                writeUnauthorized(response);
                return;
            }
            filterChain.doFilter(request, response);
        } finally {
            ThreadContext.remove();
        }
    }

    private Subject resolveSubject(HttpServletRequest request) {
        String sessionId = readSessionCookie(request);
        if (sessionId != null && !sessionId.isBlank()) {
            try {
                // Rebuild the authenticated Subject from the session id. If the session
                // is missing/expired Shiro throws, and we fall back to an anonymous Subject.
                return new Subject.Builder(securityManager).sessionId(sessionId).buildSubject();
            } catch (Exception ignored) {
                // fall through to anonymous subject
            }
        }
        // Anonymous subject; session creation disabled so anon requests don't spawn sessions.
        return new Subject.Builder(securityManager).sessionCreationEnabled(false).buildSubject();
    }

    private String readSessionCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        for (Cookie cookie : cookies) {
            if (SESSION_COOKIE_NAME.equals(cookie.getName())) {
                return cookie.getValue();
            }
        }
        return null;
    }

    private String matchAction(String path) {
        for (Map.Entry<String, String> entry : chain) {
            if (matches(entry.getKey(), path)) {
                return entry.getValue();
            }
        }
        // Safe default: require authentication for anything not explicitly listed.
        return ACTION_AUTHC;
    }

    /**
     * Ant-style pattern matching supporting {@code /**} (any depth), {@code /*} (single
     * segment) and exact matches.
     */
    private boolean matches(String pattern, String path) {
        if ("/**".equals(pattern)) {
            return true;
        }
        if (pattern.endsWith("/**")) {
            String prefix = pattern.substring(0, pattern.length() - 3);
            return path.startsWith(prefix);
        }
        if (pattern.endsWith("/*")) {
            String prefix = pattern.substring(0, pattern.length() - 2);
            if (!path.startsWith(prefix)) {
                return false;
            }
            String remainder = path.substring(prefix.length());
            return !remainder.contains("/");
        }
        return pattern.equals(path);
    }

    private void writeUnauthorized(HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"Unauthorized: authentication required\"}");
    }
}
