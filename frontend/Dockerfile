# 前端开发环境Dockerfile
# 使用国内镜像源以提高构建速度

FROM registry.cn-hangzhou.aliyuncs.com/library/node:16-alpine

# 设置工作目录
WORKDIR /app

# 设置npm镜像源
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用Nginx提供静态文件服务
FROM registry.cn-hangzhou.aliyuncs.com/library/nginx:alpine

# 复制构建产物
COPY --from=0 /app/dist /usr/share/nginx/html

# 复制Nginx配置（如果有的话）
# COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]