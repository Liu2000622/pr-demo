package com.example.scaffold.config;

import com.example.scaffold.entity.User;
import com.example.scaffold.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DataInitializer {

    @Bean
    public CommandLineRunner initData(UserRepository userRepository) {
        return args -> {
            User user = new User();
            user.setUsername("admin");
            user.setEmail("admin@example.com");
            userRepository.save(user);
        };
    }
}
