export function orderConfirmationEmailSubject(orderId: number | string) {
  return `AnimeAttire — заказ #${orderId}`;
}

export const orderConfirmationEmailHint =
  "Если у вас включены уведомления по email, подтверждение придёт в течение нескольких минут.";

