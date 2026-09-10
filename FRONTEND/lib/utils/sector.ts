/**
 * PAIMANA Infrastructure Sector Taxonomy.
 * Authoritative deterministic mapping aligning with MoSPI IPMD infrastructure classifications.
 */
export function getSectorFromAgency(agency?: string, projectName?: string): string {
  const agencyU = (agency || '').toUpperCase();
  const projU = (projectName || '').toUpperCase();

  if (
    ['NHAI', 'MORTH', 'NHIDCL', 'BRO'].some((k) => agencyU.includes(k)) ||
    ['ROAD', 'BYPASS', 'EXPRESSWAY', 'HIGHWAY', 'NH-', 'SH-'].some((k) => projU.includes(k))
  ) {
    return 'Roads & Highways';
  }

  if (
    ['RAIL', 'RVNL', 'DFCCIL', 'IRCON', 'CR', 'WR', 'NR', 'SR', 'ER', 'SECR', 'ECR', 'NCR', 'SWR', 'WCR'].some((k) => agencyU.includes(k)) ||
    ['RAILWAY', 'METRO', 'CORRIDOR', 'DOUBLING', 'GAUGE', 'LINE'].some((k) => projU.includes(k))
  ) {
    return 'Railways & Metro';
  }

  if (
    ['IOCL', 'BPCL', 'HPCL', 'ONGC', 'GAIL', 'OIL'].some((k) => agencyU.includes(k)) ||
    ['POL', 'REFINERY', 'PIPELINE', 'LPG', 'CRUDE', 'GAS'].some((k) => projU.includes(k))
  ) {
    return 'Petroleum & Natural Gas';
  }

  if (
    ['NTPC', 'PGCIL', 'POWERGRID', 'NHPC', 'THDC', 'SJVN', 'NEEPCO'].some((k) => agencyU.includes(k)) ||
    ['THERMAL', 'SUB-STATION', 'TRANSMISSION', 'HYDRO', 'POWER', 'SOLAR'].some((k) => projU.includes(k))
  ) {
    return 'Power & Energy';
  }

  if (
    ['SECL', 'CIL', 'ECL', 'BCCL', 'NCL', 'WCL', 'MCL', 'SCCL', 'NLC'].some((k) => agencyU.includes(k)) ||
    ['COAL', 'OCP', 'MINE', 'LIGNITE'].some((k) => projU.includes(k))
  ) {
    return 'Coal & Mines';
  }

  if (
    ['AAI', 'AIRPORT'].some((k) => agencyU.includes(k)) ||
    ['AIRPORT', 'RUNWAY', 'TERMINAL'].some((k) => projU.includes(k))
  ) {
    return 'Civil Aviation';
  }

  if (
    ['PORT', 'SHIPPING', 'JNPT', 'COCHIN SHIPYARD', 'VPA', 'IPA', 'DPA', 'CHPT'].some((k) => agencyU.includes(k)) ||
    ['PORT', 'BERTH', 'JETTY', 'BREAKWATER', 'DOCK'].some((k) => projU.includes(k))
  ) {
    return 'Ports & Shipping';
  }

  return 'Urban Infrastructure & Others';
}

export const ALL_SECTORS = [
  'Roads & Highways',
  'Railways & Metro',
  'Power & Energy',
  'Petroleum & Natural Gas',
  'Coal & Mines',
  'Civil Aviation',
  'Ports & Shipping',
  'Urban Infrastructure & Others'
];
