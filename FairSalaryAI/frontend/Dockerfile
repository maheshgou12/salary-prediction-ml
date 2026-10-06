# FairSalary AI Frontend - Dockerfile
FROM node:20-alpine

# Set environment variables
ENV NODE_ENV=development

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++

# Create non-root user
RUN addgroup -g 1000 -S nodejs && \
    adduser -S nextjs -u 1000 -G nodejs

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Change ownership
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]