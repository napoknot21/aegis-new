import { supabase } from '../lib/supabase';

export interface RiskCategory {
  id_cat: number;
  code: string;
  name: string;
  description: string;
}

export interface ControlDefinition {
  id_control: number;
  id_cat: number;
  code: string;
  name: string;
  unit: string;
  description: string;
  is_active: boolean;
  risk_categories?: RiskCategory;
}

export interface ControlLevel {
  id_level: number;
  id_control: number;
  id_f: number;
  level_rank: number;
  level_name: string;
  lower_bound: number;
  lower_inclusive: boolean;
  upper_bound: number;
  upper_inclusive: boolean;
  side: string;
  is_active: boolean;
  control_definitions?: ControlDefinition;
}

export async function fetchFundControls(fundId: number): Promise<ControlLevel[]> {
  const { data, error } = await supabase
    .from('control_levels')
    .select(`
      *,
      control_definitions (
        *,
        risk_categories (*)
      )
    `)
    .eq('id_f', fundId)
    .eq('is_active', true);

  if (error) {
    console.error("Error fetching fund controls:", error);
    throw error;
  }
  
  return data as ControlLevel[];
}
