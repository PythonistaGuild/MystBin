FROM grafana/grafana

# Disable Login form or not
ENV GF_AUTH_DISABLE_LOGIN_FORM "false"
# Allow anonymous authentication or not
ENV GF_AUTH_ANONYMOUS_ENABLED "false"

# Add provisioning
ADD ./provisioning /etc/grafana/provisioning
# Add configuration file
ADD ./grafana.ini /etc/grafana/grafana.ini
# Add dashboard json files
ADD ./dashboards /etc/grafana/dashboards