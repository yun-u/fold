export interface Property {
  icon: JSX.Element;
  name: string;
  content: string | JSX.Element;
}

export function Property({ properties }: { properties: Property[] }) {
  return (
    <div className="flex flex-col items-start gap-2 text-sm text-muted-foreground">
      {properties.map((property, index) => (
        <div key={index} className="flex items-start">
          <div className="flex w-32 flex-none items-center">
            <div className="mr-2">{property.icon}</div>
            <div className="truncate">{property.name}</div>
          </div>
          {property.content}
        </div>
      ))}
    </div>
  );
}
