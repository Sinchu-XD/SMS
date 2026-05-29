export function formatCurrency(amount: number, currency: 'USD' | 'INR' = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(num: number) {
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatDate(timestamp: number | string) {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(timestamp));
}
