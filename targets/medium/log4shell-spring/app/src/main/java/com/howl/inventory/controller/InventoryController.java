package com.howl.inventory.controller;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.annotation.PostConstruct;
import java.util.*;

@RestController
@RequestMapping("/api")
public class InventoryController {

    // Log4j logger - this is the vulnerable component
    private static final Logger logger = LogManager.getLogger(InventoryController.class);

    // In-memory inventory store
    private final Map<Integer, Map<String, Object>> inventory = new LinkedHashMap<>();

    @PostConstruct
    public void init() {
        inventory.put(1, createItem(1, "Wireless Keyboard", "Electronics", 29.99, 150));
        inventory.put(2, createItem(2, "USB-C Hub", "Electronics", 49.99, 75));
        inventory.put(3, createItem(3, "Standing Desk Mat", "Office", 39.99, 200));
        inventory.put(4, createItem(4, "Monitor Arm", "Office", 89.99, 50));
        inventory.put(5, createItem(5, "Noise Cancelling Headphones", "Electronics", 199.99, 30));
        inventory.put(6, createItem(6, "Webcam HD 1080p", "Electronics", 59.99, 120));
        inventory.put(7, createItem(7, "Ergonomic Mouse", "Electronics", 34.99, 90));
        inventory.put(8, createItem(8, "Desk Lamp LED", "Office", 24.99, 180));
    }

    /**
     * GET /api/items - List all inventory items.
     *
     * The X-Api-Version header value is logged directly through Log4j.
     * This is the primary Log4Shell injection point.
     */
    @GetMapping("/items")
    public ResponseEntity<?> getAllItems(
            @RequestHeader(value = "X-Api-Version", defaultValue = "1.0") String apiVersion,
            @RequestHeader(value = "User-Agent", defaultValue = "unknown") String userAgent) {

        // VULNERABLE: User-controlled header values passed directly to Log4j
        logger.info("Received API request - Version: " + apiVersion);
        logger.info("Client User-Agent: " + userAgent);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "success");
        response.put("api_version", apiVersion);
        response.put("total", inventory.size());
        response.put("items", new ArrayList<>(inventory.values()));

        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/items/{id} - Get a specific inventory item by ID.
     */
    @GetMapping("/items/{id}")
    public ResponseEntity<?> getItem(
            @PathVariable int id,
            @RequestHeader(value = "X-Api-Version", defaultValue = "1.0") String apiVersion) {

        // VULNERABLE: Header value logged through Log4j
        logger.info("Item lookup for ID: " + id + " - API Version: " + apiVersion);

        Map<String, Object> item = inventory.get(id);
        if (item == null) {
            Map<String, Object> error = new LinkedHashMap<>();
            error.put("status", "error");
            error.put("message", "Item not found with ID: " + id);
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "success");
        response.put("item", item);

        return ResponseEntity.ok(response);
    }

    /**
     * POST /api/search - Search inventory items by keyword.
     *
     * The search query is also logged through Log4j, providing another
     * injection vector via the request body.
     */
    @PostMapping("/search")
    public ResponseEntity<?> searchItems(
            @RequestBody Map<String, String> body,
            @RequestHeader(value = "X-Api-Version", defaultValue = "1.0") String apiVersion) {

        String query = body.getOrDefault("query", "");

        // VULNERABLE: Both the search query and header are logged through Log4j
        logger.info("Search request - query: " + query + " - API Version: " + apiVersion);

        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> item : inventory.values()) {
            String name = ((String) item.get("name")).toLowerCase();
            String category = ((String) item.get("category")).toLowerCase();
            if (name.contains(query.toLowerCase()) || category.contains(query.toLowerCase())) {
                results.add(item);
            }
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "success");
        response.put("query", query);
        response.put("results_count", results.size());
        response.put("results", results);

        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/status - Health check endpoint.
     * Reveals technology stack information useful for reconnaissance.
     */
    @GetMapping("/status")
    public ResponseEntity<?> status() {
        logger.info("Status check requested");

        Map<String, Object> status = new LinkedHashMap<>();
        status.put("status", "operational");
        status.put("service", "Howl Inventory API");
        status.put("version", "1.0.0");
        status.put("java_version", System.getProperty("java.version"));
        status.put("java_vendor", System.getProperty("java.vendor"));
        status.put("os_name", System.getProperty("os.name"));
        status.put("os_arch", System.getProperty("os.arch"));
        status.put("timestamp", new Date().toString());

        return ResponseEntity.ok(status);
    }

    private Map<String, Object> createItem(int id, String name, String category, double price, int quantity) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", id);
        item.put("name", name);
        item.put("category", category);
        item.put("price", price);
        item.put("quantity", quantity);
        return item;
    }
}
