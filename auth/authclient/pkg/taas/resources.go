package taas

import (
	"automation/authclient/pkg/apiclient"
	"errors"
	"fmt"
	"log"
	"net/http"
)

type resourcesClient struct {
	apiclient.ApiClient
	ServerIp string
}

func (rmc *resourcesClient) requestResource(group string, resources interface{}) error {
	url := fmt.Sprintf("http://%s/resourcesmanager/v1/res/request/%s", rmc.ServerIp, group)
	err := rmc.Call("GET", url, nil, nil, 200, resources)
	return err
}

func (rmc *resourcesClient) releaseResrouce(pool string, resourceId string) error {
	url := fmt.Sprintf("http://%s/resourcesmanager/v1/res/recycle/%s/%s", rmc.ServerIp, pool, resourceId)
	err := rmc.Call("DELETE", url, nil, nil, 200, nil)
	return err
}

type Resource struct {
	PoolId     string `json:"pool_id"`
	Id         string `json:"id"`
	Seed       string `json:"seed"`
	User       string `json:"user"`
	Password   string `json:"password"`
	CustomData struct {
		ApiAuthUrl        string `json:"api_auth_url"`
		FacAdminUser      string `json:"fac_admin_user"`
		FacAdminToken     string `json:"fac_admin_token"`
		OauthClientId     string `json:"oauth_client_id"`
		OauthClientSecret string `json:"oauth_client_secret"`
		FacIp             string `json:"fac_ip"`
		SamlSpUrl         string `json:"saml_sp_url"`
		FgtSslVpnUrl      string `json:"fgt_sslvpn_url"`
	} `json:"custom_data"`
}

type resourceNode struct {
	next *resourceNode
	data *Resource
}

type ResourceManager struct {
	resourceClient *resourcesClient
	poolHead       *resourceNode
	lastNode       *resourceNode
	poolSize       int
	nextAssign     *resourceNode
}

func (rm *ResourceManager) Init(taasIp string) {
	rm.resourceClient = &resourcesClient{
		apiclient.ApiClient{
			HttpClient:      &http.Client{},
			CloseConnection: false,
		},
		taasIp,
	}
}

func (rm *ResourceManager) Add(resource *Resource) {
	resNode := &resourceNode{
		data: resource,
		next: rm.poolHead,
	}
	if rm.poolHead == nil {
		resNode.next = resNode
		rm.poolHead = resNode
		rm.nextAssign = resNode
	}
	if rm.lastNode != nil {
		rm.lastNode.next = resNode
	}
	rm.lastNode = resNode
	rm.poolSize++
}

func (rm *ResourceManager) List() []*Resource {
	resList := []*Resource{}
	if rm.poolHead != nil {
		curr := rm.poolHead
		resList = append(resList, curr.data)
		curr = curr.next
		for {
			if curr == rm.poolHead {
				break
			}
			resList = append(resList, curr.data)
			curr = curr.next
		}
		return resList
	}
	return nil
}

func (rm *ResourceManager) Request(count int, resourceGroup string) {
	failed := 0
	for i := 0; i < count; i++ {
		res := &Resource{}
		err := rm.resourceClient.requestResource(resourceGroup, res)
		if err == nil {
			rm.Add(res)
		} else {
			fmt.Printf("Resource Request Error: %v", err)
			failed++
		}
	}
	log.Printf("Request Complete: Requested %d: Failure: %d", count-failed, failed)
}

func (rm *ResourceManager) Release() {
	resList := rm.List()
	for _, res := range resList {
		rm.resourceClient.releaseResrouce(res.PoolId, res.Id)
	}
}

func (rm *ResourceManager) Get() (*Resource, error) {
	if rm.nextAssign != nil {
		toAssign := rm.nextAssign
		rm.nextAssign = rm.nextAssign.next
		return toAssign.data, nil
	}
	return nil, errors.New("no resource to assign, pool is not inited")
}
