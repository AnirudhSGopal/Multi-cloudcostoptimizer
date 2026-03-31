import { useQuery } from '@tanstack/react-query'
import awsService from '../services/awsService'
import gcpService from '../services/gcpService'
import azureService from '../services/azureService'

export function useSecurityScan() {
  const aws = useQuery({
    queryKey: ['aws-security'],
    queryFn: () => awsService.getSecurityFindings(),
    refetchInterval: 5 * 60 * 1000, // refresh every 5 min
  })

  const gcp = useQuery({
    queryKey: ['gcp-security'],
    queryFn: () => gcpService.getSecurityFindings(),
    refetchInterval: 5 * 60 * 1000,
  })

  const azure = useQuery({
    queryKey: ['azure-security'],
    queryFn: () => azureService.getSecurityFindings(),
    refetchInterval: 5 * 60 * 1000,
  })

  const isLoading = aws.isLoading || gcp.isLoading || azure.isLoading

  return { aws, gcp, azure, isLoading }
}