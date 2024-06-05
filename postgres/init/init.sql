-- Create the 'profiles' table
CREATE TABLE IF NOT EXISTS profiles (
    profile_id SERIAL PRIMARY KEY,
    profile_name VARCHAR(255) NOT NULL,
    all_time_views INT DEFAULT 0
);

-- Create the 'profile_views' table
CREATE TABLE IF NOT EXISTS profile_views (
    view_id SERIAL PRIMARY KEY,
    viewer_profile_id INT NOT NULL,
    viewed_profile_id INT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (viewer_profile_id) REFERENCES profiles(profile_id),
    FOREIGN KEY (viewed_profile_id) REFERENCES profiles(profile_id)
);

INSERT INTO profiles (profile_name, all_time_views) VALUES
('John Doe', 5),
('Jane Smith', 3),
('Alice Johnson', 8);

INSERT INTO profile_views (viewer_profile_id, viewed_profile_id, timestamp, session_id) VALUES
(1, 2, '2023-06-01 08:30:00', 'session123'),
(1, 3, '2023-06-01 09:15:00', 'session124'),
(2, 1, '2023-06-02 10:00:00', 'session125'),
(3, 1, '2023-06-02 11:05:00', 'session126'),
(2, 3, '2023-06-02 12:45:00', 'session127');

