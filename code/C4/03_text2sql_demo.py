import os
import sys
import sqlite3

from dotenv import load_dotenv
load_dotenv()

# 添加text2sql模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'text2sql'))

from text2sql.text2sql_agent import SimpleText2SQLAgent


def setup_demo():
    """设置演示环境"""
    print("=== Text2SQL框架演示 ===\n")
    
    # 检查API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("先设置DEEPSEEK_API_KEY环境变量")
        return None
    
    # 创建演示数据库
    print("创建演示数据库...")
    db_path = create_demo_database()
    
    # 初始化Text2SQL代理
    print("初始化Text2SQL代理...")
    agent = SimpleText2SQLAgent(api_key=api_key)
    
    # 连接数据库
    print("连接数据库...")
    if not agent.connect_database(db_path):
        print("数据库连接失败!")
        return None
    
    # 加载知识库
    print("加载知识库...")
    try:
        agent.load_knowledge_base()
        print("知识库加载成功!")
    except Exception as e:
        print(f"知识库加载失败: {str(e)}")
        return None
    
    return agent, db_path


def create_demo_database():
    """创建演示数据库"""
    db_path = "text2sql_demo.db"
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            city TEXT
        )
    """)
    
    # 创建产品表
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER
        )
    """)
    
    # 创建订单表
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date TEXT,
            total_price REAL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    # 插入示例数据
    users_data = [
        (1, '张三', 'zhangsan@email.com', 25, '北京'),
        (2, '李四', 'lisi@email.com', 32, '上海'),
        (3, '王五', 'wangwu@email.com', 28, '广州'),
        (4, '赵六', 'zhaoliu@email.com', 35, '深圳'),
        (5, '陈七', 'chenqi@email.com', 29, '杭州'),
    ]
    
    products_data = [
        (1, 'iPhone 15', '电子产品', 7999.0, 50),
        (2, 'MacBook Pro', '电子产品', 12999.0, 20),
        (3, 'Nike运动鞋', '服装', 599.0, 100),
        (4, '办公椅', '家具', 899.0, 30),
        (5, '台灯', '家具', 199.0, 80),
        (6, 'iPad', '电子产品', 3999.0, 40),
        (7, 'Adidas外套', '服装', 399.0, 60),
    ]
    
    orders_data = [
        (1, 1, 1, 1, '2024-01-15', 7999.0),
        (2, 2, 3, 2, '2024-01-16', 1198.0),
        (3, 3, 5, 1, '2024-01-17', 199.0),
        (4, 1, 2, 1, '2024-01-18', 12999.0),
        (5, 4, 4, 1, '2024-01-19', 899.0),
        (6, 5, 6, 1, '2024-01-20', 3999.0),
        (7, 2, 7, 1, '2024-01-21', 399.0),
    ]
    
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_data)
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products_data)
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders_data)
    
    conn.commit()
    conn.close()
    
    print(f"演示数据库已创建: {db_path}")
    return db_path


def run_demo_queries(agent):
    """运行演示查询"""
    demo_questions = [
        "查询所有用户的姓名和邮箱",
        "年龄大于30的用户有哪些",
        "哪些产品的库存少于50",
        "查询来自北京的用户的所有订单",
        "统计每个城市的用户数量",
        "查询价格在500-8000之间的产品"
    ]
    
    print("\n开始运行演示查询...\n")
    
    success_count = 0
    
    for i, question in enumerate(demo_questions, 1):
        print(f"问题 {i}: {question}")
        print("-" * 60)
        
        try:
            result = agent.query(question)
            
            if result["success"]:
                print(f"成功! SQL: {result['sql']}")
                
                if isinstance(result["results"], dict) and "rows" in result["results"]:
                    count = result["results"]["count"]
                    print(f"返回 {count} 行数据")
                    
                    # 显示前2行数据
                    if count > 0:
                        for j, row in enumerate(result["results"]["rows"][:2]):
                            row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
                            print(f"  {j+1}. {row_str}")
                        
                        if count > 2:
                            print(f"  ... 还有 {count - 2} 行")
                else:
                    print(f"结果: {result['results']}")
                
                success_count += 1
                
            else:
                print(f"失败: {result['error']}")
                print(f"SQL: {result['sql']}")
                
        except Exception as e:
            print(f"执行错误: {str(e)}")
        
        print()
    
    # 输出统计
    total_count = len(demo_questions)


def cleanup(agent, db_path):
    """清理资源"""
    print("\n清理资源...")
    
    if agent:
        agent.cleanup()
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除演示数据库: {db_path}")


def main():
    """主函数"""
    # 设置演示环境
    setup_result = setup_demo()
    
    if setup_result is None:
        return
    
    agent, db_path = setup_result
    
    try:
        # 运行演示查询
        run_demo_queries(agent)
        
    finally:
        # 清理资源
        cleanup(agent, db_path)


if __name__ == "__main__":
    main() 

# 运行结果
# === Text2SQL框架演示 ===

# 创建演示数据库...
# 演示数据库已创建: text2sql_demo.db
# 初始化Text2SQL代理...
# Fetching 30 files: 100%|███████████████████████████████████████████████████████████████████████| 30/30 [00:00<00:00, 30218.33it/s]
# 连接数据库...
# 成功连接到数据库: text2sql_demo.db
# 加载知识库...
# You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
# 知识库数据加载完成
# 知识库加载成功!

# 开始运行演示查询...

# 问题 1: 查询所有用户的姓名和邮箱
# ------------------------------------------------------------

# === 处理查询: 查询所有用户的姓名和邮箱 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': '问题: 查询所有用户的姓名和邮箱\nSQL: SELECT name, email FROM users', 'type': 'qsql', 'score': 0.8382365703582764}, {'content': "问题: 查询某个用户的所有订单\nSQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name = '张三'", 'type': 'qsql', 'score': 0.646510124206543}, {'content': '表名: users\n表描述: 用户信息表，存储注册用户的基本信息\n字段信息:\n  - id: 用户唯一标识符，主键 (INT)\n  - name: 用户姓名，不能为空 (VARCHAR(100))\n  - email: 用户邮箱地址，必须唯一 (VARCHAR(150))\n  - age: 用户年龄 (INT)\n  - created_at: 用户注册时间 (TIMESTAMP)\n', 'type': 'description', 'score': 0.6222846508026123}, {'content': '问题: 查询每个用户的订单数量\nSQL: SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name', 'type': 'qsql', 'score': 0.6071318984031677}, {'content': '表名: users\nDDL: CREATE TABLE users (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL, email VARCHAR(150) UNIQUE, age INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)\n描述: 用户信息表，存储用户基本信息', 'type': 'ddl', 'score': 0.5879760980606079}]
# 生成SQL...
# 生成的SQL: SELECT name, email FROM users
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT name, email FROM users
# 返回 5 行数据
#   1. name: 张三 | email: zhangsan@email.com
#   2. name: 李四 | email: lisi@email.com
#   ... 还有 3 行

# 问题 2: 年龄大于30的用户有哪些
# ------------------------------------------------------------

# === 处理查询: 年龄大于30的用户有哪些 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': '问题: 查找年龄大于25岁的用户\nSQL: SELECT * FROM users WHERE age > 25', 'type': 'qsql', 'score': 0.5857226848602295}, {'content': '表名: users\n表描述: 用户信息表，存储注册用户的基本信息\n字段信息:\n  - id: 用户唯一标识符，主键 (INT)\n  - name: 用户姓名，不能为空 (VARCHAR(100))\n  - email: 用户邮箱地址，必须唯一 (VARCHAR(150))\n  - age: 用户年龄 (INT)\n  - created_at: 用户注册时间 (TIMESTAMP)\n', 'type': 'description', 'score': 0.5243154764175415}, {'content': '表名: users\nDDL: CREATE TABLE users (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL, email VARCHAR(150) UNIQUE, age INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)\n描述: 用户信息表，存储用户基本信息', 'type': 'ddl', 'score': 0.5093645453453064}, {'content': '问题: 查询所有用户的姓名和邮箱\nSQL: SELECT name, email FROM users', 'type': 'qsql', 'score': 0.45263415575027466}, {'content': "问题: 查询某个用户的所有订单\nSQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name = '张三'", 'type': 'qsql', 'score': 0.39131951332092285}]
# 生成SQL...
# 生成的SQL: SELECT * FROM users WHERE age > 30
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT * FROM users WHERE age > 30
# 返回 2 行数据
#   1. id: 2 | name: 李四 | email: lisi@email.com | age: 32 | city: 上海
#   2. id: 4 | name: 赵六 | email: zhaoliu@email.com | age: 35 | city: 深圳

# 问题 3: 哪些产品的库存少于50
# ------------------------------------------------------------

# === 处理查询: 哪些产品的库存少于50 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': '问题: 查询库存少于10的产品\nSQL: SELECT * FROM products WHERE stock < 10', 'type': 'qsql', 'score': 0.6841062307357788}, {'content': '问题: 查询价格在100到500之间的产品\nSQL: SELECT * FROM products WHERE price BETWEEN 100 AND 500', 'type': 'qsql', 'score': 0.5144352316856384}, {'content': '表名: products\n表描述: 产品表，存储商城中所有产品的信息\n字段信息:\n  - id: 产品唯一标识符，主键 (INT)\n  - name: 产品名称 (VARCHAR(200))\n  - category: 产品分类 (VARCHAR(100))\n  - price: 产品单价 (DECIMAL(10,2))\n  - stock: 库存数量 (INT)\n  - description: 产品详细描述 (TEXT)\n', 'type': 'description', 'score': 0.5013813972473145}, {'content': '表名: products\nDDL: CREATE TABLE products (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(200) NOT NULL, category VARCHAR(100), price DECIMAL(10,2), stock INT DEFAULT 0, description TEXT)\n描述: 产品表，存储产品基本信息', 'type': 'ddl', 'score': 0.4751048982143402}, {'content': '问题: 查询每个分类的产品数量\nSQL: SELECT category, COUNT(*) as product_count FROM products GROUP BY category', 'type': 'qsql', 'score': 0.45781660079956055}]
# 生成SQL...
# 生成的SQL: SELECT * FROM products WHERE stock < 50
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT * FROM products WHERE stock < 50
# 返回 3 行数据
#   1. id: 2 | name: MacBook Pro | category: 电子产品 | price: 12999.0 | stock: 20
#   2. id: 4 | name: 办公椅 | category: 家具 | price: 899.0 | stock: 30
#   ... 还有 1 行

# 问题 4: 查询来自北京的用户的所有订单
# ------------------------------------------------------------

# === 处理查询: 查询来自北京的用户的所有订单 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': "问题: 查询某个用户的所有订单\nSQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name = '张三'", 'type': 'qsql', 'score': 0.7004657983779907}, {'content': '问题: 查询每个用户的订单数量\nSQL: SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name', 'type': 'qsql', 'score': 0.6509577035903931}, {'content': '问题: 查询没有下过订单的用户\nSQL: SELECT u.* FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE o.id IS NULL', 'type': 'qsql', 'score': 0.6423381567001343}, {'content': '问题: 查询所有用户的姓名和邮箱\nSQL: SELECT name, email FROM users', 'type': 'qsql', 'score': 0.6219858527183533}, {'content': '问题: 查询订单总金额大于1000的订单\nSQL: SELECT o.*, SUM(oi.quantity * oi.unit_price) as total_amount FROM orders o JOIN order_items oi ON o.id = oi.order_id GROUP BY o.id HAVING total_amount > 1000', 'type': 'qsql', 'score': 0.6152858734130859}]
# 生成SQL...
# 生成的SQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.city = '北京'
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.city = '北京'
# 返回 2 行数据
#   1. id: 1 | user_id: 1 | product_id: 1 | quantity: 1 | order_date: 2024-01-15 | total_price: 7999.0 | user_name: 张三
#   2. id: 4 | user_id: 1 | product_id: 2 | quantity: 1 | order_date: 2024-01-18 | total_price: 12999.0 | user_name: 张三

# 问题 5: 统计每个城市的用户数量
# ------------------------------------------------------------

# === 处理查询: 统计每个城市的用户数量 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': '问题: 查询每个用户的订单数量\nSQL: SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name', 'type': 'qsql', 'score': 0.5820140242576599}, {'content': '问题: 查询所有用户的姓名和邮箱\nSQL: SELECT name, email FROM users', 'type': 'qsql', 'score': 0.5781481266021729}, {'content': '问题: 查询每个分类的产品数量\nSQL: SELECT category, COUNT(*) as product_count FROM products GROUP BY category', 'type': 'qsql', 'score': 0.5527967214584351}, {'content': '问题: 查找年龄大于25岁的用户\nSQL: SELECT * FROM users WHERE age > 25', 'type': 'qsql', 'score': 0.5508410334587097}, {'content': "问题: 查询某个用户的所有订单\nSQL: SELECT o.*, u.name as user_name FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name = '张三'", 'type': 'qsql', 'score': 0.5222238302230835}]
# 生成SQL...
# 生成的SQL: SELECT city, COUNT(*) AS user_count
# FROM users
# GROUP BY city
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT city, COUNT(*) AS user_count
# FROM users
# GROUP BY city
# 返回 5 行数据
#   1. city: 上海 | user_count: 1
#   2. city: 北京 | user_count: 1
#   ... 还有 3 行

# 问题 6: 查询价格在500-8000之间的产品
# ------------------------------------------------------------

# === 处理查询: 查询价格在500-8000之间的产品 ===
# 检索知识库...
# 检索到 5 条相关信息:
# [{'content': '问题: 查询价格在100到500之间的产品\nSQL: SELECT * FROM products WHERE price BETWEEN 100 AND 500', 'type': 'qsql', 'score': 0.7499529123306274}, {'content': '问题: 查询库存少于10的产品\nSQL: SELECT * FROM products WHERE stock < 10', 'type': 'qsql', 'score': 0.5673427581787109}, {'content': '表名: products\n表描述: 产品表，存储商城中所有产品的信息\n字段信息:\n  - id: 产品唯一标识符，主键 (INT)\n  - name: 产品名称 (VARCHAR(200))\n  - category: 产品分类 (VARCHAR(100))\n  - price: 产品单价 (DECIMAL(10,2))\n  - stock: 库存数量 (INT)\n  - description: 产品详细描述 (TEXT)\n', 'type': 'description', 'score': 0.5483654737472534}, {'content': '问题: 查询总销售额最高的前5个产品\nSQL: SELECT p.name, SUM(oi.quantity * oi.unit_price) as total_sales FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY total_sales DESC LIMIT 5', 'type': 'qsql', 'score': 0.5392488241195679}, {'content': '问题: 查询每个分类的产品数量\nSQL: SELECT category, COUNT(*) as product_count FROM products GROUP BY category', 'type': 'qsql', 'score': 0.5381777286529541}]
# 生成SQL...
# 生成的SQL: SELECT * FROM products WHERE price BETWEEN 500 AND 8000
# 执行SQL (尝试 1/3)...
# SQL执行成功!
# 成功! SQL: SELECT * FROM products WHERE price BETWEEN 500 AND 8000
# 返回 4 行数据
#   1. id: 1 | name: iPhone 15 | category: 电子产品 | price: 7999.0 | stock: 50
#   2. id: 3 | name: Nike运动鞋 | category: 服装 | price: 599.0 | stock: 100
#   ... 还有 2 行


# 清理资源...
# 数据库连接已关闭
# 知识库已清理
# 已删除演示数据库: text2sql_demo.db