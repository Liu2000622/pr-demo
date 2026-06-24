package com.example.scaffold.security;

import com.example.scaffold.entity.User;
import com.example.scaffold.repository.UserRepository;
import org.apache.shiro.authc.AuthenticationException;
import org.apache.shiro.authc.AuthenticationInfo;
import org.apache.shiro.authc.AuthenticationToken;
import org.apache.shiro.authc.SimpleAuthenticationInfo;
import org.apache.shiro.authc.UnknownAccountException;
import org.apache.shiro.authc.UsernamePasswordToken;
import org.apache.shiro.authc.credential.CredentialsMatcher;
import org.apache.shiro.authz.AuthorizationInfo;
import org.apache.shiro.authz.SimpleAuthorizationInfo;
import org.apache.shiro.lang.util.ByteSource;
import org.apache.shiro.realm.AuthorizingRealm;
import org.apache.shiro.subject.PrincipalCollection;

import java.util.Optional;

/**
 * Shiro {@link AuthorizingRealm} backed by the JPA {@link UserRepository}.
 * <p>
 * Authentication: looks the user up by username and returns a
 * {@link SimpleAuthenticationInfo} carrying the stored password hash and the user's
 * salt. The configured {@link HashedCredentialsMatcher} re-hashes the submitted
 * password with the same salt/iterations and compares it to the stored hash.
 * <p>
 * Authorization: grants the user's single stored role.
 */
public class JpaRealm extends AuthorizingRealm {

    private final UserRepository userRepository;

    public JpaRealm(UserRepository userRepository, CredentialsMatcher credentialsMatcher) {
        super(credentialsMatcher);
        this.userRepository = userRepository;
    }

    @Override
    protected AuthenticationInfo doGetAuthenticationInfo(AuthenticationToken token) throws AuthenticationException {
        UsernamePasswordToken upToken = (UsernamePasswordToken) token;
        String username = upToken.getUsername();
        // Use the list query so a duplicate (legacy) row never raises
        // NonUniqueResultException at login; the shared MySQL may carry stale dupes.
        User user = userRepository.findAllByUsername(username).stream()
                .findFirst()
                .orElseThrow(() -> new UnknownAccountException("Account not found: " + username));

        ByteSource salt = ByteSource.Util.bytes(user.getSalt());
        // principal = username, credentials = stored hex hash, salt = per-user salt.
        return new SimpleAuthenticationInfo(user.getUsername(), user.getPassword(), salt, getName());
    }

    @Override
    protected AuthorizationInfo doGetAuthorizationInfo(PrincipalCollection principals) {
        String username = (String) principals.getPrimaryPrincipal();
        SimpleAuthorizationInfo info = new SimpleAuthorizationInfo();
        Optional.ofNullable(userRepository.findAllByUsername(username).stream().findFirst().orElse(null))
                .map(User::getRole)
                .ifPresent(info::addRole);
        return info;
    }
}
