"use client"

import { useState } from "react"
import type { SearchResult } from "@/types/search"
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface SearchResultsProps {
  results: SearchResult[]
}

export function SearchResults({ results }: SearchResultsProps) {
  const [expandedResults, setExpandedResults] = useState<Record<number, boolean>>({})

  const toggleExpand = (index: number) => {
    setExpandedResults((prev) => ({
      ...prev,
      [index]: !prev[index],
    }))
  }

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <Card key={index} className="overflow-hidden">
          <CardContent className="p-0">
            <div className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <p className="font-medium">{result.content.substring(0, 100)}...</p>
                  <p className="text-sm text-gray-500 mt-1">Path: {result.path}</p>
                </div>
                <div className="ml-4 flex items-center">
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded ${
                      result.score > 90
                        ? "bg-green-100 text-green-800"
                        : result.score > 70
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {result.score}% match
                  </span>
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="flex items-center text-sm text-blue-600 hover:text-blue-800 mt-2 p-0"
                onClick={() => toggleExpand(index)}
              >
                <span>View HTML</span>
                {expandedResults[index] ? (
                  <ChevronUp className="ml-1 h-4 w-4" />
                ) : (
                  <ChevronDown className="ml-1 h-4 w-4" />
                )}
              </Button>
            </div>

            {expandedResults[index] && (
              <div className="bg-gray-50 p-4 border-t border-gray-200 overflow-x-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap">{result.html}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
