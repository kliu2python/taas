import React, { useState } from 'react';
import { Table, Button, Modal } from 'react-bootstrap';
import Slider from 'react-slick';

interface ResourceManageProps {
  nickName: string;
}

interface Resource {
  name: string;
  description: string;
  link: string;
  introImages: string[];
}

const ResourceManagement: React.FC<ResourceManageProps> = ({ nickName }) => {
  const resources: Resource[] = [
    {
      name: 'Jupyter Server',
      description: 'Access and manage files on the NFS share via the Jupyter Lab interface',
      link: 'http://10.160.13.30:8888/lab/workspaces/auto-o/tree/apks',
      introImages: [
        '/static/imgs/jupyter1.png',
        '/static/imgs/jupyter2.png',
        '/static/imgs/jupyter3.png',
      ],
    },
    {
      name: 'Jenkins Server',
      description: 'Manage continuous integration pipelines and job executions on the Jenkins server',
      link: 'http://10.160.13.30:8080/job/mobile_test/',
      introImages: [
        '/static/imgs/jenkins1.png',
        '/static/imgs/jenkins2.png',
        '/static/imgs/jenkins3.png',
      ],
    },
    {
      name: 'Android Device Farm',
      description: 'Remotely access and manage Android devices for testing on the Android Device Farm',
      link: 'http://10.160.13.230:7100/#!/devices',
      introImages: [
        '/static/imgs/stf1.png',
        '/static/imgs/stf2.png',
        '/static/imgs/stf3.png',
      ],
    },
    {
      name: 'iOS Device Farm',
      description: 'Remotely access and manage iOS devices for testing on the iOS Device Farm',
      link: 'http://10.160.13.112:9000/',
      introImages: [
        '/static/imgs/idf1.png',
        '/static/imgs/idf2.png',
        '/static/imgs/idf3.png',
      ],
    },
    {
      name: 'Failure Test Cases Screenshot Search',
      description: 'Search for and manage failure test case screenshots on the failure test case management system',
      link: 'http://10.160.24.88:31085',
      introImages: [
        '/static/imgs/search1.png',
        '/static/imgs/search2.png',
        '/static/imgs/search3.png',
      ],
    },
    {
      name: 'Add Ollama Server into VSCode as code assist',
      description: 'Step to add the Continus as the code assist to connect with Ollama server as the code assist',
      link: 'http://172.30.91.194:11434/',
      introImages: [
        '/static/imgs/continue1.png',
        '/static/imgs/continue2.png',
        '/static/imgs/continue3.png',
      ],
    },
  ];

  const [showModal, setShowModal] = useState(false);
  const [currentResource, setCurrentResource] = useState<Resource | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const handleOpenModal = (resource: Resource) => {
    setCurrentResource(resource);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setCurrentResource(null);
  };

  const carouselSettings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1,
  };

  const handleLinkClick = (link: string) => {
    window.open(link, '_blank');
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginTop: '30px' }}>
        <Table striped bordered hover responsive variant="light">
          <thead>
            <tr>
              <th>Resource Name</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {resources.map((resource, index) => (
              <tr key={index}>
                <td>{resource.name}</td>
                <td>{resource.description}</td>
                <td>
                  <Button
                    variant="primary"
                    onClick={() => handleLinkClick(resource.link)}
                  >
                    Open
                  </Button>
                  <Button
                    variant="info"
                    style={{ marginLeft: '10px' }}
                    onClick={() => handleOpenModal(resource)}
                  >
                    How to Use
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>

      {/* Modal for intro slideshow */}
      <Modal show={showModal} onHide={handleCloseModal} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>How to Use {currentResource?.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentResource && (
            <Slider {...carouselSettings}>
              {currentResource.introImages.map((image, index) => (
                <div key={index}>
                  <img
                    src={image}
                    alt={`Step ${index + 1}`}
                    style={{ width: '100%', height: 'auto', cursor: 'zoom-in' }}
                    onClick={() => setLightboxIndex(index)}
                  />
                </div>
              ))}
            </Slider>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Lightbox Modal */}
      {currentResource && (
        <Modal show={lightboxIndex !== null} onHide={() => setLightboxIndex(null)} size="xl" centered>
          <Modal.Body style={{ padding: 0, backgroundColor: '#000', position: 'relative' }}>
            <img
              src={currentResource.introImages[lightboxIndex ?? 0]}
              alt="Enlarged"
              style={{ width: '100%', height: 'auto', display: 'block', margin: '0 auto' }}
            />
            {/* Prev Button */}
            <Button
              variant="light"
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex((prev) => (prev! > 0 ? prev! - 1 : prev));
              }}
              style={{
                position: 'absolute',
                top: '50%',
                left: '10px',
                transform: 'translateY(-50%)',
                opacity: 0.8,
              }}
              disabled={lightboxIndex === 0}
            >
              ‹
            </Button>

            {/* Next Button */}
            <Button
              variant="light"
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex((prev) =>
                  prev! < currentResource.introImages.length - 1 ? prev! + 1 : prev
                );
              }}
              style={{
                position: 'absolute',
                top: '50%',
                right: '10px',
                transform: 'translateY(-50%)',
                opacity: 0.8,
              }}
              disabled={lightboxIndex === currentResource.introImages.length - 1}
            >
              ›
            </Button>
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
};

export default ResourceManagement;
