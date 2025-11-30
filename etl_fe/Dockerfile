FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Run Vite dev server exposed to host; docker-compose sets API proxy target.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
