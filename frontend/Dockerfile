# frontend/Dockerfile

# 1) Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Copy only package.json & package-lock.json first (cache mount)
COPY package*.json ./
RUN npm install

# Now copy the rest of the frontend—including "public/" and "src/"
COPY . ./

# Run the CRA build (expects public/index.html + src)
RUN npm run build

# 2) Production stage: serve with Nginx
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*

# Copy the build artifact from the "build" folder
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
