import { useQuery } from '@tanstack/react-query'
import awsService from '../services/awsService'
import gcpService from '../services/gcpService'
import azureService from '../services/azureService'
import useCloudStore from '../store/cloudStore'

export function useCostData() {
  const { selectedProvider, dateRange } = useCloudStore()

  const aws = useQuery({
    queryKey: ['aws-costs', dateRange],
    queryFn: () => awsService.getCosts({ range: dateRange }),
    enabled: selectedProvider === 'all' || selectedProvider === 'aws',
  })

  const gcp = useQuery({
    queryKey: ['gcp-costs', dateRange],
    queryFn: () => gcpService.getCosts({ range: dateRange }),
    enabled: selectedProvider === 'all' || selectedProvider === 'gcp',
  })

  const azure = useQuery({
    queryKey: ['azure-costs', dateRange],
    queryFn: () => azureService.getCosts({ range: dateRange }),
    enabled: selectedProvider === 'all' || selectedProvider === 'azure',
  })

  const isLoading = aws.isLoading || gcp.isLoading || azure.isLoading
  const isError = aws.isError || gcp.isError || azure.isError

  return { aws, gcp, azure, isLoading, isError }
}