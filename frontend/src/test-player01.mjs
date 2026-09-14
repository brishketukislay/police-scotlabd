import { api } from './api.ts';
console.log('Testing login for player01...');
api.login('player01', 'password').then(user => {
  console.log('Login successful:', user);
  console.log('Fetching player dashboard...');
  return api.playerDashboard().then(dashboard => {
    console.log('Player dashboard:', dashboard);
    console.log('Fetching reward games...');
    return api.rewardGames().then(games => {
      console.log('Reward games:', games);
      return { dashboard, games };
    });
  });
}).then(({dashboard, games}) => {
  console.log('\n--- Summary ---');
  console.log('Player XP:', dashboard?.player?.xp);
  console.log('Player weekly_xp:', dashboard?.player?.weekly_xp);
  console.log('Player achievements count:', dashboard?.player?.achievements?.length ?? 0);
  console.log('Reward games count:', games?.length ?? 0);
}).catch(err => {
  console.error('Error:', err);
});
