import { useQuery } from '@tanstack/react-query'
import cloudService from '../services/cloudService'
import useCloudStore from '../store/cloudStore'

export function useCostData() {
  const { selectedProvider, dateRange } = useCloudStore()

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