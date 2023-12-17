import { Clock9, Link, Gauge } from "lucide-react";

import { Property } from "./post-property";
import { Score } from "./score";
import { toLocaleString } from "./utils";

import { URLLink } from "@/components/url";

export function addCommonProperties(
  properteis: Property[],
  createdAt: string,
  url: string,
  score?: number,
): Property[] {
  const commonProperteis = [
    {
      icon: <Clock9 className="h-3.5 w-3.5" />,
      name: "Created",
      content: toLocaleString(createdAt),
    },
    {
      icon: <Link className="h-3.5 w-3.5" />,
      name: "URL",
      content: <URLLink href={url} />,
    },
  ];

  const scoreProperties = score
    ? [
        {
          icon: <Gauge className="h-3.5 w-3.5" />,
          name: "Score",
          content: <Score value={score} max={1} className="self-center" />,
        },
      ]
    : [];

  return [...commonProperteis, ...properteis, ...scoreProperties];
}
