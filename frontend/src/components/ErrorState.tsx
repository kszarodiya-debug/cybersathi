import { Alert } from './Alert'

export function ErrorState({ message = 'Something went wrong. Please try again.' }: { message?: string }) {
  return <Alert variant="error">{message}</Alert>
}
