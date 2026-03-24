interface Props {
  title: string;
}

export default function PlaceholderPage({ title }: Props) {
  return (
    <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h1>{title}</h1>
      <p style={{ maxWidth: '600px', lineHeight: 1.6 }}>
        Welcome to the <strong>{title}</strong> module. This section is currently under construction. 
        Please navigate to the TRADING tab to access the active features.
      </p>
    </div>
  );
}
