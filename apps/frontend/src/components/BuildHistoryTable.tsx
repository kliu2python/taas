// BuildHistoryTable.tsx
import React, { useState, useEffect } from 'react';
import { Table, Form } from 'react-bootstrap';

export interface BuildHistoryRecord {
  build_number: number;
  jenkins: {
    status: string;
    allure_url: string;
    building: boolean;
    console_url: string;
    parameters: string;
  };
  task?: any;
}

interface BuildHistoryTableProps {
  records: BuildHistoryRecord[];
}

const BuildHistoryTable: React.FC<BuildHistoryTableProps> = ({ records }) => {
  const [filterText, setFilterText] = useState<string>('');
  const [sortedRecords, setSortedRecords] = useState<BuildHistoryRecord[]>([]);
  const [sortConfig, setSortConfig] = useState<{ key: keyof BuildHistoryRecord; direction: 'ascending' | 'descending' } | null>(null);

  useEffect(() => {
    setSortedRecords(records);
  }, [records]);

  const filteredRecords = sortedRecords.filter(record =>
    record.build_number.toString().includes(filterText) ||
    record.jenkins.status.toLowerCase().includes(filterText.toLowerCase())
  );

  const requestSort = (key: keyof BuildHistoryRecord) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
    const sorted = [...sortedRecords].sort((a, b) => {
      const aValue = a[key] ?? '';
      const bValue = b[key] ?? '';
      if (aValue < bValue) {
        return direction === 'ascending' ? -1 : 1;
      }
      if (aValue > bValue) {
        return direction === 'ascending' ? 1 : -1;
      }
      return 0;
    });
    console.log(records)
    setSortedRecords(sorted);
  };

  return (
    <div>
      <Form.Group controlId="filterText">
        <Form.Control
          type="text"
          placeholder="Filter by build number or status..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
        />
      </Form.Group>
      <Table striped bordered hover className="mt-2">
        <thead>
          <tr>
            <th onClick={() => requestSort('build_number')} style={{ cursor: 'pointer' }}>
              Build Number
            </th>
            <th onClick={() => requestSort('jenkins')} style={{ cursor: 'pointer' }}>
              Status
            </th>
            <th>Allure URL</th>
            <th>Console URL</th>
            <th>Parameters</th>
          </tr>
        </thead>
        <tbody>
          {filteredRecords.map((record, index) => (
            <tr key={index}>
              <td>{record.build_number}</td>
              <td>{record.jenkins.status}</td>
              <td>
                <a href={record.jenkins.allure_url} target="_blank" rel="noopener noreferrer">
                  Link
                </a>
              </td>
              <td>
                <a href={record.jenkins.console_url} target="_blank" rel="noopener noreferrer">
                  Link
                </a>
              </td>
              <td>{record.jenkins.parameters}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
};

export default BuildHistoryTable;
