package com.example.scaffold.config;

import com.example.scaffold.repository.UserRepository;
import com.example.scaffold.security.JpaRealm;
import com.example.scaffold.security.ShiroAuthFilter;
import com.example.scaffold.service.PasswordService;
import org.apache.shiro.SecurityUtils;
import org.apache.shiro.authc.credential.HashedCredentialsMatcher;
import org.apache.shiro.crypto.hash.Sha256Hash;
import org.apache.shiro.mgt.DefaultSecurityManager;
import org.apache.shiro.realm.Realm;
import org.apache.shiro.session.mgt.DefaultSessionManager;
import org.apache.shiro.session.mgt.eis.MemorySessionDAO;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Apache Shiro configuration.
 * <p>
 * Integrates Shiro's authentication/authorization core (Realm, CredentialsMatcher,
 * SecurityManager, SessionManager) with Spring Boot 3. A custom Jakarta filter
 * ({@link ShiroAuthFilter}) enforces the URL filter chain, since the official Shiro
 * Spring Boot web starter is javax-based and incompatible with Spring Boot 3.
 * <p>
 * The filter chain explicitly lists every endpoint so that none is missed:
 * <ul>
 *   <li>{@code /api/login}, {@code /api/logout} &mdash; anonymous (login/logout endpoints)</li>
 *   <li>{@code /api/version}, {@code /api/ping} &mdash; anonymous (health/version checks)</li>
 *   <li>{@code /error} &mdash; anonymous (Spring error path)</li>
 *   <li>{@code /**} &mdash; authenticated (covers /api/hello, /api/users, /api/me and anything else)</li>
 * </ul>
 */
@Configuration
public class ShiroConfig {

    private static final long SESSION_TIMEOUT_MILLIS = 30 * 60 * 1000L;

    @Bean
    public HashedCredentialsMatcher credentialsMatcher() {
        HashedCredentialsMatcher matcher = new HashedCredentialsMatcher();
        matcher.setHashAlgorithmName(Sha256Hash.ALGORITHM_NAME);
        matcher.setHashIterations(PasswordService.ITERATIONS);
        matcher.setStoredCredentialsHexEncoded(true);
        matcher.setHashSalted(true);
        return matcher;
    }

    @Bean
    public Realm realm(UserRepository userRepository, HashedCredentialsMatcher credentialsMatcher) {
        return new JpaRealm(userRepository, credentialsMatcher);
    }

    @Bean
    public DefaultSessionManager sessionManager() {
        DefaultSessionManager sessionManager = new DefaultSessionManager();
        sessionManager.setSessionDAO(new MemorySessionDAO());
        sessionManager.setGlobalSessionTimeout(SESSION_TIMEOUT_MILLIS);
        sessionManager.setDeleteInvalidSessions(true);
        return sessionManager;
    }

    @Bean
    public DefaultSecurityManager securityManager(Realm realm, DefaultSessionManager sessionManager) {
        DefaultSecurityManager securityManager = new DefaultSecurityManager(realm);
        securityManager.setSessionManager(sessionManager);
        // Make the security manager available to SecurityUtils.getSubject() / SecurityUtils.getSecurityManager().
        SecurityUtils.setSecurityManager(securityManager);
        return securityManager;
    }

    @Bean
    public ShiroAuthFilter shiroAuthFilter(DefaultSecurityManager securityManager) {
        return new ShiroAuthFilter(securityManager, filterChain());
    }

    @Bean
    public FilterRegistrationBean<ShiroAuthFilter> shiroAuthFilterRegistration(ShiroAuthFilter shiroAuthFilter) {
        FilterRegistrationBean<ShiroAuthFilter> registration = new FilterRegistrationBean<>(shiroAuthFilter);
        registration.addUrlPatterns("/*");
        registration.setOrder(Ordered.HIGHEST_PRECEDENCE + 10);
        registration.setName("shiroAuthFilter");
        return registration;
    }

    /**
     * Ordered filter chain: anon paths first, then a catch-all requiring authentication.
     * Every controller endpoint is covered either explicitly or by the catch-all.
     */
    private Map<String, String> filterChain() {
        Map<String, String> chain = new LinkedHashMap<>();
        chain.put("/api/login", "anon");
        chain.put("/api/logout", "anon");
        chain.put("/api/version", "anon");
        chain.put("/api/ping", "anon");
        chain.put("/error", "anon");
        chain.put("/**", "authc");
        return chain;
    }
}
