package com.example.scaffold.controller;

import com.example.scaffold.entity.User;
import com.example.scaffold.repository.UserRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
public class HelloController {

    private final UserRepository userRepository;

    public HelloController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping("/hello")
    public String hello() {
        return "Hello, Spring Boot Scaffold is running!";
    }

    @GetMapping("/users")
    public List<User> getUsers() {
        return userRepository.findAll();
    }
}
