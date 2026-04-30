import http from 'k6/http';
import { check, sleep } from 'k6';

// Define profiles inline for simple tests
const profiles = {
  'staging-uk': {
    baseUrl: 'https://api.staging-uk.example.com',
    vus: 5,
    duration: '2m',
  },
  'uk-production': {
    baseUrl: 'https://api.uk.example.com',
    vus: 10,
    duration: '5m',
  },
  'i18n-production': {
    baseUrl: 'https://api.i18n.example.com',
    vus: 10,
    duration: '5m',
  },
};

const profile = profiles[__ENV.PROFILE] || profiles['staging-uk'];

export const options = {
  vus: profile.vus,
  duration: profile.duration,
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = profile.baseUrl;

export default function () {
  const res = http.get(`${BASE_URL}/orders`);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
