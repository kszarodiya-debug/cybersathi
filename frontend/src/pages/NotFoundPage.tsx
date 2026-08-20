import { Link } from 'react-router-dom'

import { Button } from '../components/Button'
import { ErrorState } from '../components/ErrorState'

export function NotFoundPage() {
  return <div className="mx-auto grid min-h-[60vh] max-w-2xl place-items-center px-5 py-20 text-center"><div><p className="text-7xl font-black text-teal">404</p><h1 className="mt-5 text-4xl font-black tracking-tight text-ink">That page took a wrong turn.</h1><div className="mt-6"><ErrorState message="The page you requested does not exist." /></div><Link className="mt-7 inline-flex" to="/"><Button type="button">Back to home</Button></Link></div></div>
}
