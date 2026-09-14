import { api } from './api';
console.log('Testing login...');
api.login('admin', 'password').then(user => {
  console.log('Login successful:', user);
  console.log('Testing me...');
  return api.me();
}).then(meUser => {
  console.log('Me successful:', meUser);
}).catch(err => {
  console.error('Error:', err);
});
