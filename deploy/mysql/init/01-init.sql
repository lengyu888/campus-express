-- 校园快递收发系统：初始化数据库字符集与时区
-- MySQL 容器首次启动时执行（MYSQL_DATABASE 已由环境变量创建）
ALTER DATABASE campus_express CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE campus_express;

SET GLOBAL time_zone = '+08:00';
