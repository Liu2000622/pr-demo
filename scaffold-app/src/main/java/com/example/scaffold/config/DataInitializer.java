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
            // Idempotent: only seed the default admin account if it does not yet exist.
            if (userRepository.findByUsername("admin").isPresent()) {
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
