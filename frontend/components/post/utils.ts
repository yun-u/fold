export function toLocaleString(dateString: string) {
  const event = new Date(Date.parse(dateString));
  const localeTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return event.toLocaleString(undefined, { timeZone: localeTimeZone });
}
