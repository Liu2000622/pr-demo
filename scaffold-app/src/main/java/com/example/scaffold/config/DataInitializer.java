package com.example.scaffold.config;

import com.example.scaffold.entity.User;
import com.example.scaffold.repository.UserRepository;
import com.example.scaffold.service.PasswordService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DataInitializer {

    @Bean
    public CommandLineRunner initData(UserRepository userRepository, PasswordService passwordService) {
        return args -> {
            // Idempotent + self-healing: the shared MySQL persists across runs, so
            // duplicate "admin" rows can accumulate. Collapse any duplicates down to a
            // single kept row before deciding whether to seed.
            java.util.List<User> existing = userRepository.findAllByUsername("admin");
            if (!existing.isEmpty()) {
                User keep = existing.get(0);
                for (User dup : existing.subList(1, existing.size())) {
                    userRepository.delete(dup);
                }
                userRepository.flush();
                // Re-seed the password/salt so the default admin always works.
                String salt = passwordService.generateSalt();
                keep.setSalt(salt);
                keep.setPassword(passwordService.hashPassword("admin123", salt));
                keep.setEmail("admin@example.com");
                keep.setRole("admin");
                userRepository.save(keep);
                return;
            }

            User user = new User();
            user.setUsername("admin");
            user.setEmail("admin@example.com");
            String salt = passwordService.generateSalt();
            user.setSalt(salt);
            user.setPassword(passwordService.hashPassword("admin123", salt));
            user.setRole("admin");
            userRepository.save(user);
        };
    }
}
