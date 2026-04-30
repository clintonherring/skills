import http from 'k6/http';
import { check, sleep } from 'k6';

// Load profile from file based on PROFILE environment variable
const profileName = __ENV.PROFILE || '{EXAMPLE}';
const profile = JSON.parse(open(`./profiles/${profileName}.json`));

export const options = {
  vus: profile.vus,
  duration: profile.duration,
  thresholds: profile.thresholds,
};

const BASE_URL = profile.baseUrl;

export default function () {
  const res = http.get(`${BASE_URL}`);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
