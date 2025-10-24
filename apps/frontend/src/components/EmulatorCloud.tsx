import React, { useEffect, useState } from 'react';
import { Button, Container, Row, Table, Col, OverlayTrigger, Tooltip } from 'react-bootstrap';
import SplitView from './SplitView';

export interface Resource {
  adb_port: number;
  available: string;
  name: string;
  status: string;
  version: string;
  vnc_port: number;
}

interface ResourcePageProps {
  resources: Resource[];
  handleNicknameSubmit: (nickname: string) => void;
  createResource: (os: string, version: string) => void;
  deleteResource: (name: string, nickName: string) => void;
  launchVNC: (port: number) => void;
  refreshPage: () => void;
  nickName: string;
  resetNickname: () => void;
  handleCreateNew: () => void;
  updateResourceStatus: (name: string, status: string) => void;
}

const ResourcePage: React.FC<ResourcePageProps> = ({
  resources,
  createResource,
  deleteResource,
  launchVNC,
  refreshPage,
  nickName,
  resetNickname,
  handleCreateNew,
  updateResourceStatus,
  handleNicknameSubmit,
}) => {
  const [resourceStatuses, setResourceStatuses] = useState<{ [name: string]: boolean }>({});
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null); // Track selected resource for VNC

  useEffect(() => {
    const savedStatuses = localStorage.getItem('resourceStatuses');
    if (savedStatuses) {
      setResourceStatuses(JSON.parse(savedStatuses));
    }

    const enableLaunchButtons = () => {
      setResourceStatuses((prevStatuses) => {
        const updatedStatuses = resources.reduce((acc: { [name: string]: boolean }, resource) => {
          acc[resource.name] = true;
          return acc;
        }, {});
        localStorage.setItem('resourceStatuses', JSON.stringify(updatedStatuses));
        return updatedStatuses;
      });
    };

    const timeoutId = setTimeout(enableLaunchButtons, 5000);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [resources, updateResourceStatus]);

  const handleLaunchVNC = (resource: Resource) => {
    setSelectedResource(resource); // Set the selected resource to show in SplitView
  };

  const handleGoBack = () => {
    setSelectedResource(null); // Reset when going back
  };

  const launchNFS = () => {
    window.open('http://10.160.13.30:8888/lab/tree/apks', '_blank');
  };

  return (
    <Container fluid>
      {/* Only show buttons if no resource is selected */}
      {!selectedResource && (
        <Row className="mb-3">
          <Col>
            <div className="d-flex gap-2">
              <Button onClick={handleCreateNew} disabled={!nickName}>
                Create New Resource
              </Button>
              <Button variant="info" onClick={refreshPage}>
                Refresh
              </Button>
              <Button variant="secondary" onClick={launchNFS}>
                NFS Location
              </Button>
            </div>
          </Col>
        </Row>
      )}

      {/* Show SplitView if a resource has been selected for VNC */}
      {selectedResource ? (
        <SplitView
          resource={selectedResource}
          launchVNC={launchVNC}
          onGoBack={handleGoBack} // Pass "Go Back" functionality to SplitView
        />
      ) : (
        <>
          {nickName ? (
            <Table striped bordered hover responsive>
              <thead className="table-dark">
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Version</th>
                  <th className="text-center">VNC Port</th>
                  <th className="text-center">ADB Port</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {resources.length > 0 ? (
                  resources.map((resource) => (
                    <tr
                      key={resource.name}
                      className={resource.status === 'active' ? 'table-success' : ''}
                    >
                      <td>{resource.name}</td>
                      <td>{resource.status}</td>
                      <td>{resource.version}</td>
                      <td className="text-center">{resource.vnc_port}</td>
                      <td className="text-center">{resource.adb_port}</td>
                      <td>
                        <div className="d-flex gap-2">
                          <OverlayTrigger
                            overlay={
                              <Tooltip>
                                {resourceStatuses[resource.name]
                                  ? 'Launch the VNC viewer.'
                                  : 'Wait for the resource to become available.'}
                              </Tooltip>
                            }
                          >
                            <Button
                              variant="primary"
                              onClick={() => handleLaunchVNC(resource)} // Pass resource to handle launch
                              disabled={!resourceStatuses[resource.name]}
                            >
                              Launch
                            </Button>
                          </OverlayTrigger>
                          <Button
                            variant="danger"
                            onClick={() => deleteResource(resource.name, nickName)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="text-center text-muted">
                      No resources available.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          ) : (
            <div className="text-center mt-4">
              <h5 className="text-warning">Login your nickname first to access resources.</h5>
            </div>
          )}
        </>
      )}
    </Container>
  );
};

export default ResourcePage;
