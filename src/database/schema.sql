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
  `original_price` DECIMAL(10,2) NOT NULL,
  `discount_rate` DECIMAL(10,2) NOT NULl,
  `quantity_available` INT NOT NULL,
  `rating_avg` REAL NOT NULL DEFAULT 0.0,
  `rating_count` INT NOT NULL,
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
  `applied_discounts` INT NOT NULL,
  `total_price` REAL NOT NULL,
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

CREATE TABLE IF NOT EXISTS `invoices` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `address_id` INT,
  `issue_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` VARCHAR(50),
  `payment_summary` TEXT,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orders` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `payment_type` VARCHAR(50) NOT NULL,
  `order_status` VARCHAR(50) NOT NULL,
  `order_created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `invoice_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
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
  `owner_id` INT NOT NULL,
  `owner_type` ENUM('USER', 'MERCHANT') NOT NULL,
  `balance` DECIMAL(18,2) DEFAULT 0.00,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `payments` (
  `id` INT AUTO_INCREMENT NOT NULL UNIQUE,
  `sender_id` INT NOT NULL,
  `sender_type` ENUM('USER', 'MERCHANT') NOT NULL,
  `receiver_id` INT NOT NULL,
  `receiver_type` ENUM('USER', 'MERCHANT') NOT NULL,
  `type` VARCHAR(50) NOT NULL,
  `amount` DECIMAL(18,2) NOT NULL,
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

CREATE TABLE IF NOT EXISTS `inventories` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `product_id` INT,
  `quantity_available` INT,
  `quantity_reserved` INT,
  PRIMARY KEY (`id`)
  FOREIGN KEY(`product_id`)  REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `inventory_addresses` (
  `inventory_id` INT NOT NULL, 
  `address_id` INT NOT NULL,
  PRIMARY KEY (`inventory_id`, `address_id`),
  FOREIGN KEY (`inventory_id`) REFERENCES `inventories`(`id`)
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
  PRIMARY KEY(`product_id`, `image_id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`image_id`) REFERENCES `images`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `product_metadata` (
  `id` INT NOT NULL,
  `product_id` INT NOT NULL,
  `view_count` INT,
  `sold_count` INT,
  `add_to_cart_count` INT,
  `wishlist_count` INT,
  `click_through_rate` REAL,
  `popularity_score` REAL,
  `keywords` TEXT,
  `embedding_vector` TEXT,
  `tags` TEXT,
  `demographics_fit` TEXT,
  `seasonal_relevance` TEXT,
  PRIMARY KEY(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `reviews` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `user_id` INT,
  `ratings` REAL,
  `description` TEXT,
  `likes` INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_reviews` (
  `user_id` INT NOT NULL,
  `review_id` INT NOT NULL,
  PRIMARY KEY(`user_id`, `review_id`),
  FOREIGN KEY (`review_id`) REFERENCES `reviews`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `review_images` (
  `review_id` INT NOT NULL,
  `image_id` INT NOT NULL,
  PRIMARY KEY(`review_id`, `image_id`),
  FOREIGN KEY (`image_id`) REFERENCES `images`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`review_id`) REFERENCES `reviews`(`id`)
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

CREATE TABLE IF NOT EXISTS `voucher` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `merchant_id` INT,
  `type` VARCHAR(50),
  `active_until` DATETIME,
  `cashback` REAL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_vouchers` (
  `user_id` INT NOT NULL,
  `voucher_id` INT NOT NULL,
  PRIMARY KEY(`user_id`, `voucher_id`),
  FOREIGN KEY (`voucher_id`) REFERENCES `voucher`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `merchant_inventories` (
  `merchant_id` INT NOT NULL,
  `inventory_id` INT NOT NULL,
  PRIMARY KEY(`merchant_id`, `inventory_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`inventory_id`) REFERENCES `inventories`(`id`)
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

CREATE TABLE IF NOT EXISTS `merchant_vouchers` (
  `merchant_id` INT NOT NULL,
  `voucher_id` INT NOT NULL,
  PRIMARY KEY(`merchant_id`, `voucher_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (`voucher_id`) REFERENCES `voucher`(`id`)
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
