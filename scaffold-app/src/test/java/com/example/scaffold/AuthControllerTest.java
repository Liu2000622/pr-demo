package com.example.scaffold;

import com.example.scaffold.service.CaptchaService;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Verifies the Shiro-based authentication flow: anonymous endpoints, protected endpoints
 * requiring authentication, captcha-gated login & registration, authenticated access,
 * and logout.
 */
@SpringBootTest
@AutoConfigureMockMvc
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private CaptchaService captchaService;

    @Test
    void anonymousEndpointsAreAccessibleWithoutAuth() throws Exception {
        mockMvc.perform(get("/api/version"))
                .andExpect(status().isOk())
                .andExpect(content().string("v1.0"));
        mockMvc.perform(get("/api/ping"))
                .andExpect(status().isOk())
                .andExpect(content().string("pong"));
    }

    @Test
    void captchaEndpointReturnsImage() throws Exception {
        mockMvc.perform(get("/api/captcha"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.captchaId").isNotEmpty())
                .andExpect(jsonPath("$.image").value(org.hamcrest.Matchers.startsWith("data:image/png;base64,")));
    }

    @Test
    void protectedEndpointsReturn401WithoutAuth() throws Exception {
        mockMvc.perform(get("/api/users")).andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/hello")).andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/me")).andExpect(status().isUnauthorized());
    }

    @Test
    void loginWithoutCaptchaIsRejected() throws Exception {
        mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content("{\"username\":\"admin\",\"password\":\"admin123\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void loginWithWrongCaptchaIsRejected() throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content(loginBody("admin", "admin123", captcha.id(), "WRONG")))
                .andExpect(status().isBadRequest());
    }

    @Test
    void captchaIsSingleUse() throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        // First use (wrong password, but captcha accepted) consumes the captcha.
        mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content(loginBody("admin", "wrong", captcha.id(), captcha.text())))
                .andExpect(status().isUnauthorized());
        // Second use of the same captcha id must now fail with bad captcha, not 401.
        mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content(loginBody("admin", "admin123", captcha.id(), captcha.text())))
                .andExpect(status().isBadRequest());
    }

    @Test
    void loginWithInvalidCredentialsReturns401() throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content(loginBody("admin", "wrong", captcha.id(), captcha.text())))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void loginThenAccessProtectedEndpoints() throws Exception {
        Cookie session = login("admin", "admin123");
        assertThat(session).isNotNull();
        assertThat(session.getValue()).isNotBlank();

        mockMvc.perform(get("/api/users").cookie(session)).andExpect(status().isOk());
        mockMvc.perform(get("/api/hello").cookie(session)).andExpect(status().isOk());
        mockMvc.perform(get("/api/me").cookie(session))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("admin"))
                .andExpect(jsonPath("$.authenticated").value(true));
    }

    @Test
    void logoutInvalidatesSession() throws Exception {
        Cookie session = login("admin", "admin123");

        mockMvc.perform(post("/api/logout").cookie(session))
                .andExpect(status().isOk());

        // The old session id must no longer grant access.
        mockMvc.perform(get("/api/users").cookie(session))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void registerCreatesLoginableUser() throws Exception {
        String username = "tester" + System.nanoTime();
        CaptchaService.Captcha captcha = captchaService.generate();
        mockMvc.perform(post("/api/register")
                        .contentType(APPLICATION_JSON)
                        .content(registerBody(username, "secret123", captcha.id(), captcha.text())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.username").value(username));

        // The newly registered user can log in.
        Cookie session = login(username, "secret123");
        assertThat(session.getValue()).isNotBlank();
        mockMvc.perform(get("/api/me").cookie(session))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value(username))
                .andExpect(jsonPath("$.authenticated").value(true));
    }

    @Test
    void registerRejectsDuplicateUsername() throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        mockMvc.perform(post("/api/register")
                        .contentType(APPLICATION_JSON)
                        .content(registerBody("admin", "secret123", captcha.id(), captcha.text())))
                .andExpect(status().isConflict());
    }

    @Test
    void registerRejectsShortPassword() throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        mockMvc.perform(post("/api/register")
                        .contentType(APPLICATION_JSON)
                        .content(registerBody("shortuser", "123", captcha.id(), captcha.text())))
                .andExpect(status().isBadRequest());
    }

    private Cookie login(String username, String password) throws Exception {
        CaptchaService.Captcha captcha = captchaService.generate();
        MvcResult result = mockMvc.perform(post("/api/login")
                        .contentType(APPLICATION_JSON)
                        .content(loginBody(username, password, captcha.id(), captcha.text())))
                .andExpect(status().isOk())
                .andReturn();
        return result.getResponse().getCookie("SHIRO_SESSION_ID");
    }

    private static String loginBody(String username, String password, String captchaId, String captcha) {
        return "{\"username\":\"" + username + "\",\"password\":\"" + password
                + "\",\"captchaId\":\"" + captchaId + "\",\"captcha\":\"" + captcha + "\"}";
    }

    private static String registerBody(String username, String password, String captchaId, String captcha) {
        return "{\"username\":\"" + username + "\",\"password\":\"" + password
                + "\",\"captchaId\":\"" + captchaId + "\",\"captcha\":\"" + captcha + "\"}";
    }
}
