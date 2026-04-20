module.exports = {
  apps: [
    {
      name: 'institutional-backend',
      script: 'server.py',
      interpreter: 'python3',
      cwd: '/Users/mac/institutional-footprint',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      restart_delay: 5000,
      min_uptime: '10s',
      max_restarts: 10
    },
    {
      name: 'institutional-dashboard',
      script: 'npm',
      args: 'start',
      cwd: '/Users/mac/institutional-footprint/web-dashboard',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PORT: 3001,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000'
      },
      error_file: './logs/dashboard-error.log',
      out_file: './logs/dashboard-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      restart_delay: 5000,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
};
