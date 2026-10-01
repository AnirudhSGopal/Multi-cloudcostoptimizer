import { useQuery } from '@tanstack/react-query'
import cloudService from '../services/cloudService'

export function useCostData() {
  const accountsQuery = useQuery({
    queryKey: ['cloud-accounts'],
    queryFn: () => cloudService.getAccounts(),
    refetchInterval: 5 * 60 * 1000,
  })

  return {
    accounts: accountsQuery.data?.data?.accounts || [],
    isLoading: accountsQuery.isLoading,
    isError: accountsQuery.isError,
    refetch: accountsQuery.refetch,
  }
}