"use client";

import {
  createContext,
  useReducer,
  Dispatch,
  ReactNode,
  useContext,
} from "react";

const SearchContext = createContext<SearchParams | null>(null);

const SearchDispatchContext = createContext<Dispatch<SearchAction> | null>(
  null,
);

export function useSearch() {
  return useContext(SearchContext);
}

export function useSearchDispatch() {
  return useContext(SearchDispatchContext);
}

export function SearchProvider({ children }: { children: ReactNode }) {
  const [searchParams, dispatch] = useReducer(reducer, initialSearchParams);

  return (
    <SearchContext.Provider value={searchParams}>
      <SearchDispatchContext.Provider value={dispatch}>
        {children}
      </SearchDispatchContext.Provider>
    </SearchContext.Provider>
  );
}

export interface SearchParams {
  author: string;
  bookmarked: boolean;
  category: string[];
  desc: boolean;
  text: string;
  title: string;
  unread: boolean;
  vector_search: string;
  vector_search_document: string;
}

const searchParamsKeys: Set<string> = new Set([
  "author",
  "bookmarked",
  "category",
  "desc",
  "text",
  "title",
  "unread",
  "vector_search",
  "vector_search_document",
]);

const initialSearchParams: SearchParams = {
  author: "",
  bookmarked: false,
  category: [],
  desc: true,
  text: "",
  title: "",
  unread: true,
  vector_search: "",
  vector_search_document: "",
};

type SearchActionMap = {
  [K in keyof SearchParams]: { type: K; value: SearchParams[K] };
} & { reset: { type: "reset" } };

type SearchAction = SearchActionMap[keyof SearchActionMap];

function reducer(
  searchParams: SearchParams,
  action: SearchAction,
): SearchParams {
  if (action.type == "reset") {
    if (searchParams.vector_search_document) {
      return {
        ...initialSearchParams,
        unread: false,
        vector_search_document: searchParams.vector_search_document,
      };
    }

    if (searchParams.vector_search) {
      return {
        ...initialSearchParams,
        vector_search: searchParams.vector_search,
      };
    }

    return initialSearchParams;
  }

  if (!searchParamsKeys.has(action.type)) {
    throw new Error(`Unhandled action type: ${action.type}`);
  }

  if (action.type === "vector_search_document") {
    return {
      ...searchParams,
      unread: false,
      vector_search: "",
      [action.type]: action.value,
    };
  }

  return {
    ...searchParams,
    [action.type]: action.value,
  };
}
