FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Expose the port
EXPOSE 3000

# Command to run the application
CMD ["npm", "start"]
