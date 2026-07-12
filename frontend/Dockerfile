FROM caddy:2-alpine AS static-server

COPY Caddyfile.preview /etc/caddy/Caddyfile
COPY out /srv

EXPOSE 80
