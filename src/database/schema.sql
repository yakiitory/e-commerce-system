CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `hash` VARCHAR(255) NOT NULL,
  `last_login` DATETIME,
  `is_active` BOOLEAN,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `age` INT NOT NULL,
  `gender` VARCHAR(20) NOT NULL,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `phone_number` VARCHAR(20) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `addresses` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `house_no` VARCHAR(50) NOT NULL,
  `street` VARCHAR(100) NOT NULL,
  `city` VARCHAR(100) NOT NULL,
  `postal_code` VARCHAR(20) NOT NULL,
  `additional_notes` VARCHAR(255),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_addresses` (
  `user_id` INT NOT NULL,
  `address_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `address_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `merchants` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'merchant',
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `hash` VARCHAR(255) NOT NULL,
  `last_login` DATETIME,
  `is_active` BOOLEAN,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `store_name` VARCHAR(100) NOT NULL,
  `ratings` REAL DEFAULT 0.0,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `phone_number` VARCHAR(20) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `merchant_addresses` (
  `merchant_id` INT NOT NULL,
  `address_id` INT NOT NULL,
  PRIMARY KEY (`merchant_id`, `address_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `hash` VARCHAR(255) NOT NULL,
  `last_login` DATETIME,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `logs` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `target_type` VARCHAR(50) NOT NULL,
  `target_id` INT NOT NULL,
  `details` TEXT,
  `status` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `admin_logs` (
  `admin_id` INT NOT NULL,
  `log_id` INT NOT NULL,
  PRIMARY KEY (`admin_id`, `log_id`),
  FOREIGN KEY (`admin_id`) REFERENCES `admins`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`log_id`) REFERENCES `logs`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `categories` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `name` VARCHAR(100),
  `parent_id` INT,
  `description` TEXT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `products` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `name` VARCHAR(150) NOT NULl,
  `brand` VARCHAR(100) NOT NULL,
  `category_id` INT NOT NULL,
  `description` TEXT NOT NULl,
  `price` DECIMAL(10,2) NOT NULL,
  `quantity_available` INT NOT NULL,
  `rating_score` REAL NOT NULL DEFAULT 0.0,
  `rating_count` INT NOT NULL DEFAULT 0,
  `merchant_id` INT NOT NULL,
  `address_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `items` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `product_id` INT NOT NULL,
  `product_quantity` INT NOT NULL,
  `product_price` REAL NOT NULL,
  `applied_discounts` INT NOT NULL DEFAULT 0,
  `total_price` REAL NOT NULL DEFAULT 0.0,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `carts` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `cart_items` (
  `cart_id` INT NOT NULL,
  `item_id` INT NOT NULL,
  PRIMARY KEY (`cart_id`, `item_id`),
  FOREIGN KEY (`cart_id`) REFERENCES `carts`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`item_id`) REFERENCES `items`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orders` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `user_id` INT NOT NULL,
  `merchant_id` INT NOT NULL,
  `shipping_address_id` INT NOT NULL,
  `billing_address_id` INT NOT NULL,
  `total_amount` DECIMAL(10,2) NOT NULL,
  `status` TINYINT NOT NULL,
  `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `shipments` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `order_id` INT NOT NULL,
  `status` VARCHAR(50) NOT NULL,
  `estimated_date` DATETIME,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `order_items` (
  `order_id` INT NOT NULL,
  `item_id` INT NOT NULL,
  PRIMARY KEY (`order_id`, `item_id`),
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`item_id`) REFERENCES `items`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_orders` (
  `user_id` INT NOT NULL,
  `order_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `order_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `virtualcards` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `balance` DECIMAL(18,2) DEFAULT 0.00,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_virtualcards` (
  `user_id` INT NOT NULL,
  `virtualcard_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `virtualcard_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`virtualcard_id`) REFERENCES `virtualcards`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `merchant_virtualcards` (
  `merchant_id` INT NOT NULL,
  `virtualcard_id` INT NOT NULL,
  PRIMARY KEY (`merchant_id`, `virtualcard_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`virtualcard_id`) REFERENCES `virtualcards`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `payments` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `sender_id` INT NOT NULL,
  `sender_type` VARCHAR(50) NOT NULL,
  `receiver_id` INT NOT NULL,
  `receiver_type` VARCHAR(50) NOT NULL,
  `amount` DECIMAL(18,2) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS `shipment_addresses` (
  `shipment_id` INT NOT NULL,
  `address_id` INT NOT NULL,
  PRIMARY KEY(`shipment_id`, `address_id`),
  FOREIGN KEY (`shipment_id`) REFERENCES `shipments`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `images` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `url` TEXT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `product_images` (
  `product_id` INT NOT NULL,
  `image_id` INT NOT NULL,
  `is_thumbnail` INT NOT NULL,
  PRIMARY KEY(`product_id`, `image_id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`image_id`) REFERENCES `images`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `product_metadata` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `product_id` INT NOT NULL,
  `view_count` INT,
  `sold_count` INT,
  `add_to_cart_count` INT,
  `wishlist_count` INT,
  `click_through_rate` REAL,
  `popularity_score` REAL,
  PRIMARY KEY(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `reviews` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `user_id` INT,
  `product_id` INT,
  `ratings` REAL,
  `description` TEXT,
  `likes` INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_viewedproducts` (
  `user_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  PRIMARY KEY(`user_id`, `product_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_likedproducts` (
  `user_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  PRIMARY KEY(`user_id`, `product_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_metadata` (
  `user_id` INT NOT NULL UNIQUE,
  `price_sensitivity` REAL NOT NULL,
  `engagement_score` REAL,
  `recency_decay_factor` REAL,
  `interest_vector` TEXT,
  `segment_label` TEXT,
  `churn_risk_score` REAL,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `invoices` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `order_id` INT NOT NULL,
  `address_id` INT,
  `issue_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  `status` TINYINT,
  `payment_summary` TEXT,
  PRIMARY KEY(`id`),
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `merchant_products` (
  `merchant_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  PRIMARY KEY(`merchant_id`, `product_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS `history` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `user_id` INT NOT NULL,
  `interaction_type` VARCHAR(50),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
