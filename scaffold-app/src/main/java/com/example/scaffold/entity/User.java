package com.example.scaffold.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

@Data
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String username;

    private String email;

    /** Hex-encoded SHA-256 hash of the password (salted, 1024 iterations). */
    private String password;

    /** Per-user salt used when hashing the password. */
    private String salt;

    /** Role assigned to the user, used by Shiro for authorization. */
    private String role;
}
