# Stage 1: Build react app
FROM node:18-alpine AS build
WORKDIR /app

# 1) Copy package.json & package-lock.json, install dependencies
COPY package*.json ./
RUN npm install

# 2) Copy everything else (including public/ and src/)
COPY . ./

# 3) Run the React build
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
# Remove default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy the build artifacts from the "build" folder
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 3000 (Nginx will listen here)
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
