/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.springframework.context.annotation.Configuration
 *  org.springframework.messaging.simp.config.MessageBrokerRegistry
 *  org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker
 *  org.springframework.web.socket.config.annotation.StompEndpointRegistry
 *  org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer
 */
package org.example.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig
implements WebSocketMessageBrokerConfigurer {
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint(new String[]{"/ws"}).setAllowedOriginPatterns(new String[]{"*"}).withSockJS();
        System.out.println("\u2705 WebSocket \u044d\u043d\u0434\u043f\u043e\u0438\u043d\u0442 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d: /ws");
    }

    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker(new String[]{"/topic"});
        registry.setApplicationDestinationPrefixes(new String[]{"/app"});
        System.out.println("\u2705 \u0411\u0440\u043e\u043a\u0435\u0440 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0439 \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043d: /topic");
    }
}
