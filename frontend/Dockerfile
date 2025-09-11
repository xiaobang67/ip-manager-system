# 前端开发环境Dockerfile
# 使用国内镜像源以提高构建速度

FROM node:16-alpine

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

# 确保 vite 可执行并构建应用
RUN node node_modules/vite/bin/vite.js build

# 使用Nginx提供静态文件服务
FROM nginx:alpine

# 复制构建产物
COPY --from=0 /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]